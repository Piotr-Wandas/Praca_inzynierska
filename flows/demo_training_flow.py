from prefect import flow, task
from financial_platform.modeling.demo_pipeline import run_demo

@task(retries=1)
def validate_and_train():
    return run_demo()

@flow(name="semester2-demo-training")
def demo_training_flow():
    return validate_and_train()

if __name__ == "__main__":
    demo_training_flow()
