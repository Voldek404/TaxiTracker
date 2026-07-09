from locust import HttpUser, task, constant

class WebsiteUser(HttpUser):
    wait_time = constant(0)
    host = "http://127.0.0.1:8000"

    @task
    def demo(self):
        print("TASK EXECUTED")
        response = self.client.get("/demo/live/")
        print(response.status_code)


# from locust import HttpUser, task
#
#
# class WebsiteUser(HttpUser):
#     host = "http://127.0.0.1:8000"
#
#     def on_start(self):
#         # Получаем csrftoken
#         self.client.get("/api/v1/token/")
#
#         csrf_token = self.client.cookies.get("csrftoken")
#
#         # Логинимся
#         self.client.post(
#             "/login/",
#             data={
#                 "username": "manager_1",
#                 "password": "051587asd",
#             },
#             headers={
#                 "X-CSRFToken": csrf_token,
#                 "Referer": f"{self.host}/login/",
#             },
#         )
#
#     @task
#     def update_timezone(self):
#         csrf_token = self.client.cookies.get("csrftoken")
#
#         self.client.post(
#             "/enterprise/1/timezone/",
#             json={"timezone": "UTC"},
#             headers={
#                 "X-CSRFToken": csrf_token,
#                 "Referer": f"{self.host}/enterprise/1/timezone/",
#             },
#         )