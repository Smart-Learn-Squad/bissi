from core.memory.conversation_store import ConversationStore


def test_conversation_store_round_trip(tmp_path):
    store = ConversationStore(db_path=tmp_path / "conversations.db")
    conversation_id = store.create_conversation("Demo")
    store.save_message(conversation_id, "user", "Bonjour")
    store.save_message(conversation_id, "assistant", "Salut", metadata={"tool_calls": []})

    history = store.get_history(conversation_id)
    recent = store.get_recent_conversations()

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["metadata"] == {"tool_calls": []}
    assert recent[0]["title"] == "Demo"
