"""Insert clearly synthetic demonstration tickets through the real API."""
import argparse
import json
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:3000")
args = parser.parse_args()
records = [
    ("Library Wi-Fi keeps disconnecting", "network", "high", "open", "Aisha Khan", "Central Library", "Unassigned"),
    ("Projector display flickers in Lab 3", "hardware", "medium", "in_progress", "Rohan Mehta", "Engineering / Lab 3", "IT Support"),
    ("Student portal account locked", "access", "urgent", "open", "Meera Iyer", "Administration", "Unassigned"),
    ("Python environment setup for workshop", "software", "low", "resolved", "Arjun Rao", "Computer Lab 2", "IT Support"),
    ("Printer queue stuck in department office", "hardware", "medium", "in_progress", "Sara Ali", "Science Block", "IT Support"),
    ("Guest network access for visiting faculty", "network", "low", "open", "Dev Patel", "Seminar Hall", "Unassigned"),
    ("License renewal for design software", "software", "high", "open", "Nisha Sharma", "Design Studio", "Unassigned"),
    ("Email password reset request", "access", "medium", "resolved", "Kabir Das", "Student Centre", "IT Support"),
]
existing = json.load(urllib.request.urlopen(args.url + "/api/tickets?limit=100"))
titles = {ticket["title"] for ticket in existing}
count = 0
for title, category, priority, status, requester, location, assignee in records:
    if title in titles:
        continue
    body = {"title": title, "category": category, "priority": priority, "status": status,
            "requester": requester, "location": location, "assignee": assignee,
            "description": "Synthetic demonstration ticket for the CampusDesk capstone."}
    request = urllib.request.Request(args.url + "/api/tickets", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request) as response:
        assert response.status == 201
    count += 1
print(f"Created {count} synthetic tickets at {args.url}")
