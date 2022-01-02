import itertools
import sys
import asyncio

# Async spinner print
spinner = itertools.cycle(['ᕕ(⌐■_■)ᕗ',
                           'ᕙ(⌐■_■)ง',
                           'ᕕ(■_■¬)╯',
                           'ᕙ(■_■¬)~'])
async def spinner_wait():
    while True:
        next_spinner = next(spinner)
        sys.stdout.write(next_spinner)
        sys.stdout.flush()
        for x in next_spinner: sys.stdout.write('\b')
        await asyncio.sleep(0.3)

class Spinner():
    def __init__(self):
        pass
    def __enter__(self):
        # starting a spinner
        self.spinner = asyncio.ensure_future(spinner_wait())
    def __exit__(self, type, value, traceback):
        # got what we needed so we cancel the spinner
        self.spinner.cancel()
