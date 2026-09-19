from locust import HttpUser, task, between

class IIPMPUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        self.client.get("/dashboard/")

    @task(4)
    def view_projects_list(self):
        self.client.get("/projects/")

    @task(2)
    def search_projects(self):
        self.client.get("/api/search/?q=Kolkata")

    @task(1)
    def view_analytics(self):
        self.client.get("/analytics/")
