from python_terraform import *


def create_resources(template: str, variables: dict) -> str:
    count = 0
    while count < 10:
        tf = Terraform()
        tf.init(template)
        _, stdout, stderr = tf.apply(
            template,
            capture_output=True,
            no_color=IsFlagged,
            skip_plan=True,
            state=f"{template.split('/')[-1]}.tfstate",
            var=variables)
        if stdout:
            return stdout
        elif stderr:
            count += 1
            continue
        return stderr


def destroy_resources(template: str, variables: dict) -> str:
    count = 0
    while count < 10:
        tf = Terraform()
        _, stdout, stderr = tf.destroy(
            template,
            capture_output=False,
            no_color=IsFlagged,
            state=f"{template.split('/')[-1]}.tfstate",
            var=variables)
        if stdout:
            return stdout
        elif stderr:
            count += 1
            continue
        return stderr