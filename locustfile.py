from locust import HttpUser, task
import os
import time

headers = {
    "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY2NjIzNTY1NiwianRpIjoiMjgxOTU3MTEtMWY5Ny00MGU4LWE5ZDEtNTAwNTYwNDFiY2QwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJpZCI6MSwidXNlcm5hbWUiOiJqYXZpZXJsZyJ9LCJuYmYiOjE2NjYyMzU2NTZ9.Zw4GAS18j_NeVd5HMSo9f09Klmh6LC_N_AMx63fS2sg"
}

filename = "./sample.mp3"
# Check file size
file_size = os.path.getsize(filename)
if file_size == 0:
    raise Exception("File is empty")


class Benchy(HttpUser):
    @task
    def blow_it_up(self):
        with open(filename, "rb") as f:
            files = {"fileName": f}
            form_data = {"newFormat": "wav"}
            response = self.client.post(
                url="/api/tasks",
                headers=headers,
                files=files,
                data=form_data,
            )
            time.sleep(10)
