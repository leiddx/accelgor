"""验证应用能正常启动（含 Tortoise 生命周期）并正确响应基础请求。"""


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
