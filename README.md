# textual-spectess
Tool to calibrate TESS-W sensor spectral response, written in Textual

# enviromental file
.env file shoudl contain:

```bash
REF_ENDPOINT=serial:/dev/ttyUSB0:9600
TEST_ENDPOINT=udp:192.168.4.1:2255
DATABASE_URL=sqlite+aiosqlite:///spectess.db
```

# Notes

from [Tasck Overflow](https://stackoverflow.com/questions/71631247/textual-python-tui-enabling-long-running-external-asyncio-functionality)
Textual widgets have an internal message queue that processes events sequentially. Your on_mount handler is processing one of these events, but because it is an infinite loop, you are preventing further events for being processed.

If you want to process something in the background you will need to creat a new asyncio Task. Note that you can’t await that task, since that will also prevent the handler from returning.

```bash
textual console
textual run --dev -c spectess --textual --log-file kk.log
```

Prepare migrations with alembic
```bash
alembic init -t async src/migrations
```