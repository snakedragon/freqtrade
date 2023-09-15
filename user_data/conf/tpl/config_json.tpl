

{
    "max_open_trades": -1,
    "stake_currency": "USDT",
    "stake_amount": {{stake_amount}},
    "tradable_balance_ratio": 0.99,
    "timeframe": "1m",
    "dry_run": true,
    "dry_run_wallet": 10000,
    "cancel_open_orders_on_exit": false,
    "trading_mode": "futures",
    "margin_mode": "isolated",
    "unfilledtimeout": {
        "entry": 6,
        "exit": 6,
        "exit_timeout_count": 6,
        "unit": "seconds"
    },
    "entry_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1,
        "price_last_balance": 0.0,
        "check_depth_of_market": {
            "enabled": false,
            "bids_to_ask_delta": 1
        }
    },
    "exit_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1
    },
    "indicator_data": {{indicator_data}},
    "entry_signal_data": {{entry_signal_data}},
    "extract_signal_data": {{extract_signal_data}},
    "exchange": {
        "name": "{{exchange.name}}",
        "key": "{{exchange.key}}",
        "secret": "{{exchange.secret}}",
        "ccxt_config": {},
        "ccxt_async_config": {},
        "pair_whitelist": [
            "ETH/USDT:USDT",
            "BTC/USDT:USDT"
        ],
        "pair_blacklist": []
    },
    "pairlists": [
        {
            "method": "StaticPairList"
        }
    ],
    "telegram": {
        "enabled": false,
        "token": "",
        "chat_id": ""
    },
    "api_server": {
        "enabled": true,
        "listen_ip_address": "0.0.0.0",
        "listen_port": {{port}},
        "verbosity": "error",
        "enable_openapi": false,
        "jwt_secret_key": "87e522866f8e8524dc2beca26bada09971835b7c4c3ca055a0c2b8e2ed1e7563",
        "ws_token": "ryeV8C5DVoiLzb3jFIDlRXZCJp9WSI-xiQ",
        "CORS_origins": ["http://192.168.35.137:8080"],
        "username": "ft",
        "password": "ft"
    },
    "bot_name": "ftbot_{{seqNo}}",
    "db_url": "sqlite:///user_data/db/tradesv3_{{seqNo}}.db",
    "initial_state": "running",
    "log_file": "user_data/logs/ftbot_{{seqNo}}.log",
    "force_entry_enable": false,
    "internals": {
        "process_throttle_secs": 3
    }
}