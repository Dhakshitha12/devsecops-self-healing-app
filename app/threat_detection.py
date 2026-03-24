def detect_threat(text):

    threats = ["malware", "attack", "breach", "hacked", "unauthorized", "virus"]

    text = text.lower()

    for word in threats:
        if word in text:
            return "HIGH"

    return "LOW"