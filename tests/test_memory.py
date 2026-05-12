from src.memory import count_signals_for_run, init_memory_db, write_signal


def test_count_signals_for_run_only_counts_matching_run(tmp_path):
    memory_db = tmp_path / "memory.db"
    init_memory_db(str(memory_db))

    write_signal("low_performer", "signal 1", run_id="run-a", db_path=str(memory_db))
    write_signal("trend_alert", "signal 2", run_id="run-b", db_path=str(memory_db))
    write_signal("budget_realloc", "signal 3", run_id="run-a", db_path=str(memory_db))

    assert count_signals_for_run("run-a", db_path=str(memory_db)) == 2
    assert count_signals_for_run("run-b", db_path=str(memory_db)) == 1
