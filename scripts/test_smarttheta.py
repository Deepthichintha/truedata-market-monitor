import asyncio

from app.services.smarttheta import SmartThetaClient


async def main():
    client = SmartThetaClient()

    print("=" * 60)
    print("SmartTheta Market Integration Test")
    print("=" * 60)

    print("\nTesting latest AARTIIND data...")

    data = await client.get_market_data("AARTIIND")

    print("Symbol:", data["symbol"])
    print("TrueData ID:", data["truedata_symbol_id"])
    print("LTP:", data["ltp"])
    print("Timestamp:", data["timestamp"])

    print("\nTesting AARTIIND history...")

    history = await client.get_market_history(
        "AARTIIND",
        limit=5,
    )

    print("History count:", history["count"])

    for tick in history["data"]:
        print(
            tick["timestamp"],
            "| LTP:",
            tick["ltp"],
            "| Volume:",
            tick["total_volume"],
        )

    print("\nTesting live market data...")

    live = await client.get_live_market_data()

    print("Live symbols:", live["count"])

    print("\nIntegration test completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
