import asyncio

asynk def hello_world():
    print('hello world')

loop = asyncio.get_event_loop()
loop.run_until_complete(hello_world())
loop.close()

