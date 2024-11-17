# conda create --name venv python=3.10
# conda activate venv
# rasa run --cors "*"

# import os
#
# license_key = os.environ.get('OPEN_API_KEY')
# if license_key:
#     print(license_key)
# else:
#     print("License Key is not set.")

import asyncio

async def main():
    print("Hello, world!")

# Chạy vòng lặp sự kiện
if __name__ == "__main__":
    asyncio.run(main())
