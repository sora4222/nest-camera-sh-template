import threading

from camwatch.state_requests import StateRequests


def test_names_asked_for_are_taken_once_oldest_first():
    requests = StateRequests()
    requests.ask("on_break")
    requests.ask("working")
    assert requests.take() == ["on_break", "working"]
    assert requests.take() == []


def test_asking_from_many_threads_loses_nothing():
    requests = StateRequests()
    threads = [threading.Thread(target=requests.ask, args=(str(n),)) for n in range(50)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(requests.take(), key=int) == [str(n) for n in range(50)]
