"""The file protocol, against a fake bridge that answers like creaper_bridge.lua."""
import json
import os
import threading
import time

import pytest

from creaper.bridge import Bridge, BridgeError


def write_atomic(path, text):
    """Like the Lua bridge's write_file: temp file, then rename over. False if
    something (a client, a virus scanner) holds the files right now."""
    tmp = path.with_name(path.name + ".fake.tmp")
    try:
        tmp.write_text(text)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def claim(path):
    """Like the bridge's claim-by-rename. If the claimed file can't be read yet
    (a scanner has it open), put it back for the next round."""
    claimed = path.with_name(path.name + ".claimed")
    try:
        os.replace(path, claimed)
    except OSError:
        return None
    try:
        req = json.loads(claimed.read_text())
    except (OSError, ValueError):
        try:
            os.replace(claimed, path)
        except OSError:
            pass
        return None
    try:
        claimed.unlink()
    except OSError:
        pass
    return req


def fake_bridge(directory, protocol, stop, answer=lambda req: {"ok": True, "result": req["cmd"]}):
    (directory / "requests").mkdir(exist_ok=True)
    (directory / "responses").mkdir(exist_ok=True)

    unsent = []  # like the bridge: answers that couldn't be written yet, retried

    def run():
        while not stop.is_set():
            write_atomic(directory / "bridge.json", json.dumps({"protocol": protocol, "time": time.time()}))
            unsent[:] = [(path, text) for path, text in unsent if not write_atomic(path, text)]
            if protocol >= 2:
                pending = [(p, directory / "responses" / p.name) for p in (directory / "requests").glob("*.json")]
            else:
                pending = [(directory / "request.json", directory / "response.json")]
            for request, response in pending:
                req = claim(request) if request.exists() else None
                if req:
                    text = json.dumps({"id": req["id"], **answer(req)})
                    if not write_atomic(response, text):
                        unsent.append((response, text))
            time.sleep(0.005)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


@pytest.mark.parametrize("protocol", [1, 2])
def test_calls_round_trip(tmp_path, protocol):
    stop = threading.Event()
    fake_bridge(tmp_path, protocol, stop)
    try:
        time.sleep(0.05)
        assert Bridge(tmp_path).call("ping") == "ping"
    finally:
        stop.set()


def test_many_clients_at_once_get_their_own_answers(tmp_path):
    stop = threading.Event()
    fake_bridge(tmp_path, 2, stop, answer=lambda req: {"ok": True, "result": req["params"]["n"]})
    time.sleep(0.05)
    results, errors = {}, []

    def client(n):
        try:
            results[n] = Bridge(tmp_path).call("echo", {"n": n}, timeout=10)
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=client, args=(n,)) for n in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    stop.set()
    assert not errors and results == {n: n for n in range(20)}
    assert not list((tmp_path / "responses").glob("*.json"))  # every answer collected


def test_errors_and_timeouts(tmp_path):
    stop = threading.Event()
    fake_bridge(tmp_path, 2, stop, answer=lambda req: {"ok": False, "error": "there is no track 9"})
    time.sleep(0.05)
    try:
        with pytest.raises(BridgeError, match="no track 9"):
            Bridge(tmp_path).call("get_track_details")
    finally:
        stop.set()
    time.sleep(0.05)
    (tmp_path / "bridge.json").write_text(json.dumps({"protocol": 2, "time": time.time()}))
    with pytest.raises(BridgeError, match="didn't answer"):
        Bridge(tmp_path).call("ping", timeout=0.3)
    assert not list((tmp_path / "requests").glob("*.json"))  # unanswered request withdrawn


def test_not_running(tmp_path):
    with pytest.raises(BridgeError, match="isn't answering"):
        Bridge(tmp_path).call("ping")


def frozen_heartbeat(directory, age):
    """The last beat a bridge wrote while recording, before REAPER's save/delete
    prompt opened and stopped it."""
    (directory / "bridge.json").write_text(json.dumps(
        {"protocol": 2, "time": time.time() - age, "recording": True, "stop_prompt": True}))


def test_waits_for_the_user_to_answer_the_recording_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr("creaper.bridge.HEARTBEAT_MAX_AGE", 0.2)
    frozen_heartbeat(tmp_path, age=1)
    stop = threading.Event()
    threading.Timer(0.8, lambda: fake_bridge(tmp_path, 2, stop)).start()  # the user answers
    waits = []
    try:
        assert Bridge(tmp_path).call("recording_status", timeout=0.3, on_user_wait=lambda: waits.append(1)) \
            == "recording_status"
    finally:
        stop.set()
    assert waits == [1]


def test_waits_when_the_prompt_opens_mid_call(tmp_path, monkeypatch):
    monkeypatch.setattr("creaper.bridge.HEARTBEAT_MAX_AGE", 0.2)
    frozen_heartbeat(tmp_path, age=0)  # fresh: the prompt opens just after this
    stop = threading.Event()
    threading.Timer(1.0, lambda: fake_bridge(tmp_path, 2, stop)).start()
    try:
        # The timeout passes while the prompt is open; the call keeps waiting.
        assert Bridge(tmp_path).call("transport", timeout=0.3) == "transport"
    finally:
        stop.set()


def test_gives_up_on_an_unanswered_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr("creaper.bridge.HEARTBEAT_MAX_AGE", 0.2)
    monkeypatch.setattr("creaper.bridge.STOP_PROMPT_WAIT", 0.5)
    frozen_heartbeat(tmp_path, age=1)
    with pytest.raises(BridgeError, match="save or delete"):
        Bridge(tmp_path).call("recording_status", timeout=0.3)
    frozen_heartbeat(tmp_path, age=0)
    with pytest.raises(BridgeError, match="save or delete"):
        Bridge(tmp_path).call("recording_status", timeout=0.3)
    assert not list((tmp_path / "requests").glob("*.json"))


def test_tells_the_caller_even_when_the_user_answers_quickly(tmp_path, monkeypatch):
    monkeypatch.setattr("creaper.bridge.HEARTBEAT_MAX_AGE", 0.2)
    frozen_heartbeat(tmp_path, age=0)
    stop = threading.Event()
    threading.Timer(1.0, lambda: fake_bridge(tmp_path, 2, stop)).start()
    waits = []
    try:
        # Answered well within the usual timeout, but the caller still hears about the wait.
        assert Bridge(tmp_path).call("recording_status", timeout=30, on_user_wait=lambda: waits.append(1)) \
            == "recording_status"
    finally:
        stop.set()
    assert waits == [1]
