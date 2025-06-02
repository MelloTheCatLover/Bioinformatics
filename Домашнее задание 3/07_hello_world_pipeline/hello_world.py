from dagster import job, op

@op
def hello(context):
    context.log.info("Hello!")

@job
def my_job():
    hello()
