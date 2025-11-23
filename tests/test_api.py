from fastapi.testclient import TestClient

def test_full_flow(client: TestClient):
    # 1. Создаем команду
    team_payload = {
        "team_name": "dev-team-1",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": True},
            {"user_id": "u2", "username": "Bob", "is_active": True},
            {"user_id": "u3", "username": "Charlie", "is_active": True},
        ]
    }
    response = client.post("/team/add", json=team_payload)
    assert response.status_code == 201
    assert response.json()["team"]["team_name"] == "dev-team-1"
    assert len(response.json()["team"]["members"]) == 3

    # 2. Проверяем, что команда создалась
    response = client.get(f"/team/get?team_name=dev-team-1")
    assert response.status_code == 200
    assert response.json()["team_name"] == "dev-team-1"

    # 3. Создаем PR от имени Alice (u1)
    pr_payload = {
        "pull_request_id": "pr1",
        "pull_request_name": "Feature X",
        "author_id": "u1"
    }
    response = client.post("/pullRequest/create", json=pr_payload)
    assert response.status_code == 201
    pr_response = response.json()["pr"]
    assert pr_response["pull_request_id"] == "pr1"
    assert pr_response["author_id"] == "u1"
    
    # 4. Проверяем, что назначено 2 ревьюера, и это не автор
    reviewers = pr_response["assigned_reviewers"]
    assert len(reviewers) == 2
    assert "u1" not in reviewers
    assert "u2" in reviewers or "u3" in reviewers

    # 5. Проверяем, что у одного из ревьюеров есть PR на ревью
    reviewer_to_check = reviewers[0]
    response = client.get(f"/users/getReview?user_id={reviewer_to_check}")
    assert response.status_code == 200
    review_list = response.json()
    assert review_list["user_id"] == reviewer_to_check
    assert len(review_list["pull_requests"]) == 1
    assert review_list["pull_requests"][0]["pull_request_id"] == "pr1"

    # 6. Мержим PR
    response = client.post("/pullRequest/merge", json={"pull_request_id": "pr1"})
    assert response.status_code == 200
    assert response.json()["pr"]["status"] == "MERGED"

    # 7. Пытаемся переназначить ревьюера на замерженном PR (должна быть ошибка)
    reassign_payload = {"pull_request_id": "pr1", "old_user_id": reviewers[0]}
    response = client.post("/pullRequest/reassign", json=reassign_payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PR_MERGED"
