from app.services.guidance.safety import destroys_evidence, drop_evidence_destruction, scrub_reply


def test_detects_destruction_advice():
    assert destroys_evidence("Delete the suspicious link from your device")
    assert destroys_evidence("Block the sender and delete the message after taking a screenshot")
    assert destroys_evidence("Factory-reset your phone immediately")


def test_allows_negated_advice():
    assert not destroys_evidence("Do not delete the chats, messages or call logs.")
    assert not destroys_evidence("Never wipe the device before evidence is preserved")
    assert not destroys_evidence("Keep the screenshots safe")


def test_filters_lists_and_replies():
    items = ["Change your password", "Delete the SMS", "Don't delete anything"]
    assert drop_evidence_destruction(items) == ["Change your password", "Don't delete anything"]
    assert scrub_reply("Call your bank. Then delete the chat. Keep screenshots.") == "Call your bank. Keep screenshots."
