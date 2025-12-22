import time
import hmac
import hashlib
import base64
import requests
import json
import math
from dotenv import load_dotenv
import os

load_dotenv()  # 默认读取当前目录下的 .env

api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")
access_passphrase = os.getenv("ACCESS_PASSPHRASE")


def generate_signature(secret_key, timestamp, method, request_path, query_string, body):
  message = timestamp + method.upper() + request_path + query_string + str(body)
  signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
  # print(base64.b64encode(signature).decode())
  return base64.b64encode(signature).decode()


def generate_signature_get(secret_key, timestamp, method, request_path, query_string):
  message = timestamp + method.upper() + request_path + query_string
  signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
  # print(base64.b64encode(signature).decode())
  return base64.b64encode(signature).decode()


def send_request_post(api_key, secret_key, access_passphrase, method, request_path, query_string, body):
  timestamp = str(int(time.time() * 1000))
  # print(timestamp)
  body = json.dumps(body)
  signature = generate_signature(secret_key, timestamp, method, request_path, query_string, body)

  headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
  }

  url = "https://api-contract.weex.com/"  # Please replace with the actual API address
  if method == "GET":
    response = requests.get(url + request_path, headers=headers)
  elif method == "POST":
    response = requests.post(url + request_path, headers=headers, data=body)
  return response

def send_request_get(api_key, secret_key, access_passphrase, method, request_path, query_string):
  timestamp = str(int(time.time() * 1000))
  # print(timestamp)
  signature = generate_signature_get(secret_key, timestamp, method, request_path, query_string)

  headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "zh-CN"
  }

  url = "https://api-contract.weex.com/"  # Please replace with the actual API address
  if method == "GET":
    response = requests.get(url + request_path+query_string, headers=headers)
  return response


def check_balance():
    # 调用账户资产查询接口
    request_path = "/capi/v2/account/assets"
    query_string = ""
    response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
    print(response.status_code)
    print(response.text)


def get_price(symbol):
    """
    获取标的当前行情价格等信息
    :param symbol: 交易对，例如 'cmt_btcusdt'
    :return: 解析后的 JSON 数据（dict）
    """
    request_path = "/capi/v2/market/ticker"
    query_string = f"?symbol={symbol}"
    response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def change_leverage(symbol, margin_mode, long_leverage, short_leverage=None):
    """
    调整杠杆倍数
    :param symbol: 交易对，例如 'cmt_btcusdt'
    :param margin_mode: 保证金模式，1：全仓，3：逐仓
    :param long_leverage: 多头杠杆，例如 '2'
    :param short_leverage: 空头杠杆，例如 '2'；在全仓模式下必须与 long_leverage 相同
    """
    if short_leverage is None:
        short_leverage = long_leverage

    request_path = "/capi/v2/account/leverage"
    body = {
        "symbol": symbol,
        "marginMode": margin_mode,
        "longLeverage": str(long_leverage),
        "shortLeverage": str(short_leverage)
    }
    query_string = ""
    response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
    print(response.status_code)
    print(response.text)

def get():
    # Example of calling a GET request
    request_path = "/capi/v2/account/position/singlePosition"
    query_string = '?symbol=cmt_btcusdt'
    response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
    print(response.status_code)
    print(response.text)

def post():
    # Example of calling a POST request
    request_path = "/capi/v2/order/placeOrder"
    body = {
	"symbol": "cmt_btcusdt",
	"client_oid": "71557515757447",
	"size": "0.01",
	"type": "1",
	"order_type": "0",
	"match_price": "1",
	"price": "80000"}
    query_string = ""
    response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
    print(response.status_code)
    print(response.text)


def place_order(symbol, client_oid, size, order_type, match_price, price, type_order, preset_take_profit_price=None, preset_stop_loss_price=None, margin_mode=None):
    """
    下单
    :param symbol: 交易对，例如 'cmt_btcusdt'
    :param client_oid: 自定义订单ID（不超过40个字符）
    :param size: 订单数量（不能为零或负数）
    :param order_type: 订单类型 0: 普通, 1: 只做Maker, 2: Fill-Or-Kill, 3: Immediate Or Cancel
    :param match_price: 0: 限价, 1: 市价
    :param price: 订单价格（限价单必填，精度和步长遵循合约信息接口）
    :param type_order: 1: 开多, 2: 开空, 3: 平多, 4: 平空
    :param preset_take_profit_price: 预设止盈价格（可选）
    :param preset_stop_loss_price: 预设止损价格（可选）
    :param margin_mode: 保证金模式 1: 全仓, 3: 逐仓，默认为1（全仓）
    :return: 解析后的 JSON 数据（dict）
    """
    request_path = "/capi/v2/order/placeOrder"
    body = {
        "symbol": symbol,
        "client_oid": client_oid,
        "size": str(size),
        "type": str(type_order),
        "order_type": str(order_type),
        "match_price": str(match_price),
        "price": str(price)
    }
    
    if preset_take_profit_price is not None:
        body["presetTakeProfitPrice"] = str(preset_take_profit_price)
    if preset_stop_loss_price is not None:
        body["presetStopLossPrice"] = str(preset_stop_loss_price)
    if margin_mode is not None:
        body["marginMode"] = margin_mode
    
    query_string = ""
    response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def cancel_order(order_id=None, client_oid=None):
    """
    取消订单
    :param order_id: 订单ID（orderId 或 clientOid 必须提供一个）
    :param client_oid: 客户端自定义ID（orderId 或 clientOid 必须提供一个）
    :return: 解析后的 JSON 数据（dict）
    """
    if order_id is None and client_oid is None:
        raise ValueError("Either order_id or client_oid must be provided")
    
    request_path = "/capi/v2/order/cancel_order"
    body = {}
    if order_id:
        body["orderId"] = str(order_id)
    if client_oid:
        body["clientOid"] = str(client_oid)
    
    query_string = ""
    response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def cancel_batch_orders(ids=None, cids=None):
    """
    批量取消订单
    :param ids: 订单ID列表（ids 或 cids 必须提供一个）
    :param cids: 客户端自定义ID列表（ids 或 cids 必须提供一个）
    :return: 解析后的 JSON 数据（dict）
    """
    if ids is None and cids is None:
        raise ValueError("Either ids or cids must be provided")
    
    request_path = "/capi/v2/order/cancel_batch_orders"
    body = {}
    if ids:
        body["ids"] = [str(id) for id in ids]
    if cids:
        body["cids"] = [str(cid) for cid in cids]
    
    query_string = ""
    response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def get_order_detail(order_id):
    """
    查询指定订单
    :param order_id: 订单ID
    :return: 解析后的 JSON 数据（dict）
    """
    request_path = "/capi/v2/order/detail"
    query_string = f"?orderId={order_id}"
    response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def get_order_history(symbol=None, page_size=None, create_date=None):
    """
    获取历史挂单
    :param symbol: 交易对（可选）
    :param page_size: 每页数量（可选）
    :param create_date: 创建时间，Unix毫秒时间戳（可选，必须≤90且不能为负数）
    :return: 解析后的 JSON 数据（list）
    """
    request_path = "/capi/v2/order/history"
    params = []
    if symbol:
        params.append(f"symbol={symbol}")
    if page_size:
        params.append(f"pageSize={page_size}")
    if create_date:
        params.append(f"createDate={create_date}")
    
    query_string = "?" + "&".join(params) if params else ""
    response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def get_current_orders(symbol=None, order_id=None, start_time=None, end_time=None, limit=None, page=None):
    """
    获取当前挂单
    :param symbol: 交易对（可选）
    :param order_id: 订单ID（可选）
    :param start_time: 查询记录开始时间，Unix毫秒时间戳（可选）
    :param end_time: 查询记录结束时间，Unix毫秒时间戳（可选）
    :param limit: 限制数量，默认100，最大100（可选）
    :param page: 页码，默认0（可选）
    :return: 解析后的 JSON 数据（list）
    """
    request_path = "/capi/v2/order/current"
    params = []
    if symbol:
        params.append(f"symbol={symbol}")
    if order_id:
        params.append(f"orderId={order_id}")
    if start_time:
        params.append(f"startTime={start_time}")
    if end_time:
        params.append(f"endTime={end_time}")
    if limit:
        params.append(f"limit={limit}")
    if page is not None:
        params.append(f"page={page}")
    
    query_string = "?" + "&".join(params) if params else ""
    response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def cancel_all_orders(cancel_order_type, symbol=None):
    """
    撤销全部订单
    :param cancel_order_type: 取消订单类型 'normal': 取消普通订单, 'plan': 取消触发/计划订单
    :param symbol: 交易对（可选，如果不提供则取消所有交易对的订单）
    :return: 解析后的 JSON 数据（list）
    """
    request_path = "/capi/v2/order/cancelAllOrders"
    body = {
        "cancelOrderType": cancel_order_type
    }
    if symbol:
        body["symbol"] = symbol
    
    query_string = ""
    response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def close_positions(symbol=None):
    """
    一键平仓
    :param symbol: 交易对（可选，如果不提供则以市价平掉所有持仓）
    :return: 解析后的 JSON 数据（list）
    """
    request_path = "/capi/v2/order/closePositions"
    body = {}
    if symbol:
        body["symbol"] = symbol
    
    query_string = ""
    response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def get_order_fills(symbol=None, order_id=None, start_time=None, end_time=None, limit=None):
    """
    获取订单成交明细
    :param symbol: 交易对名称（可选）
    :param order_id: 订单ID（可选）
    :param start_time: 开始时间戳，Unix毫秒时间戳（可选）
    :param end_time: 结束时间戳，Unix毫秒时间戳（可选）
    :param limit: 查询数量，最大100，默认100（可选）
    :return: 解析后的 JSON 数据（dict）
    """
    request_path = "/capi/v2/order/fills"
    params = []
    if symbol:
        params.append(f"symbol={symbol}")
    if order_id:
        params.append(f"orderId={order_id}")
    if start_time:
        params.append(f"startTime={start_time}")
    if end_time:
        params.append(f"endTime={end_time}")
    if limit:
        params.append(f"limit={limit}")
    
    query_string = "?" + "&".join(params) if params else ""
    response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
    print(response.status_code)
    print(response.text)
    try:
        return response.json()
    except ValueError:
        return None


def adjust_price_to_step_size(price, step_size=0.1):
    """
    调整价格以符合步长要求
    :param price: 原始价格
    :param step_size: 步长，默认0.1
    :return: 调整后的价格（向下取整到最近的步长倍数）
    """
    # 向下取整到最近的步长倍数
    adjusted_price = math.floor(price / step_size) * step_size
    # 保留适当的小数位数（根据步长确定）
    if step_size >= 1:
        decimal_places = 0
    elif step_size >= 0.1:
        decimal_places = 1
    elif step_size >= 0.01:
        decimal_places = 2
    elif step_size >= 0.001:
        decimal_places = 3
    else:
        decimal_places = 4
    
    return round(adjusted_price, decimal_places)


def get_current_price_and_place_limit_order(symbol, size, order_type_direction, price_offset_percent=20, step_size=0.1):
    """
    获取当前真实价格并挂一个不会立即成交的限价单
    :param symbol: 交易对，例如 'cmt_btcusdt'
    :param size: 订单数量
    :param order_type_direction: 订单方向 1: 开多, 2: 开空, 3: 平多, 4: 平空
    :param price_offset_percent: 价格偏移百分比，默认20%（开多时价格低于市价，开空时价格高于市价）
    :param step_size: 价格步长，默认0.1
    :return: 订单结果（dict）
    """
    # 1. 获取当前价格
    print(f"\n=== 步骤1: 获取 {symbol} 当前价格 ===")
    price_info = get_price(symbol)
    if not price_info:
        print("获取价格失败")
        return None
    
    current_price = float(price_info.get("last", 0))
    best_bid = float(price_info.get("best_bid", current_price))
    best_ask = float(price_info.get("best_ask", current_price))
    
    print(f"当前价格: {current_price}")
    print(f"最佳买价: {best_bid}")
    print(f"最佳卖价: {best_ask}")
    
    # 2. 计算限价单价格（确保不会立即成交）
    # 开多：价格低于最佳买价
    # 开空：价格高于最佳卖价
    if order_type_direction == 1:  # 开多
        limit_price = best_bid * (1 - price_offset_percent / 100)
        print(f"\n=== 步骤2: 挂开多限价单（价格低于市价 {price_offset_percent}%） ===")
    elif order_type_direction == 2:  # 开空
        limit_price = best_ask * (1 + price_offset_percent / 100)
        print(f"\n=== 步骤2: 挂开空限价单（价格高于市价 {price_offset_percent}%） ===")
    elif order_type_direction == 3:  # 平多
        limit_price = best_bid * (1 - price_offset_percent / 100)
        print(f"\n=== 步骤2: 挂平多限价单（价格低于市价 {price_offset_percent}%） ===")
    elif order_type_direction == 4:  # 平空
        limit_price = best_ask * (1 + price_offset_percent / 100)
        print(f"\n=== 步骤2: 挂平空限价单（价格高于市价 {price_offset_percent}%） ===")
    else:
        print(f"无效的订单方向: {order_type_direction}")
        return None
    
    # 3. 调整价格以符合步长要求
    limit_price_adjusted = adjust_price_to_step_size(limit_price, step_size)
    print(f"计算出的限价单价格: {limit_price}")
    print(f"调整后的限价单价格（符合步长 {step_size}）: {limit_price_adjusted}")
    
    # 确保价格大于0
    if limit_price_adjusted <= 0:
        print(f"错误: 调整后的价格 {limit_price_adjusted} 必须大于0")
        return None
    
    # 4. 生成客户端订单ID
    client_oid = f"{int(time.time() * 1000)}_{order_type_direction}"
    
    # 5. 下单
    print(f"\n=== 步骤3: 提交限价单 ===")
    order_result = place_order(
        symbol=symbol,
        client_oid=client_oid,
        size=str(size),
        order_type="0",  # 0: 普通限价单
        match_price="0",  # 0: 限价
        price=str(limit_price_adjusted),
        type_order=str(order_type_direction)
    )
    
    if order_result:
        print(f"订单提交成功!")
        print(f"订单ID: {order_result.get('order_id')}")
        print(f"客户端订单ID: {order_result.get('client_oid')}")
    else:
        print("订单提交失败")
    
    return order_result


def place_market_order_open_short_and_close(symbol="cmt_btcusdt", size="0.0002", wait_seconds=1):
    """
    市价开空订单，等待指定时间后立即平仓并检查确认
    :param symbol: 交易对，默认 'cmt_btcusdt'
    :param size: 订单数量，默认 0.0002
    :param wait_seconds: 等待时间（秒），默认1秒
    :return: (开仓订单结果, 平仓订单结果)
    """
    print("\n" + "="*60)
    print("市价开空并平仓流程 - 开始")
    print("="*60)
    
    # 1. 获取当前价格
    print(f"\n【步骤1】获取 {symbol} 当前价格")
    price_info = get_price(symbol)
    if not price_info:
        print("获取价格失败")
        return None, None
    
    current_price = float(price_info.get("last", 0))
    print(f"当前价格: {current_price}")
    
    # 2. 市价开空订单
    print(f"\n【步骤2】提交市价开空订单（数量: {size}）")
    client_oid_open = f"{int(time.time() * 1000)}_open_short"
    
    open_order_result = place_order(
        symbol=symbol,
        client_oid=client_oid_open,
        size=str(size),
        order_type="0",  # 0: 普通订单
        match_price="1",  # 1: 市价
        price="0",  # 市价单时价格可以为0
        type_order="2"  # 2: 开空
    )
    
    if not open_order_result or not open_order_result.get('order_id'):
        print("开空订单提交失败")
        return None, None
    
    open_order_id = open_order_result.get('order_id')
    print(f"✓ 开空订单提交成功!")
    print(f"  订单ID: {open_order_id}")
    print(f"  客户端订单ID: {open_order_result.get('client_oid')}")
    
    # 3. 等待指定时间
    print(f"\n【步骤3】等待 {wait_seconds} 秒...")
    time.sleep(wait_seconds)
    
    # 4. 检查开仓订单状态
    print(f"\n【步骤4】检查开仓订单状态")
    open_order_detail = get_order_detail(open_order_id)
    if open_order_detail:
        print(f"订单状态: {open_order_detail.get('status')}")
        print(f"已成交数量: {open_order_detail.get('filled_qty')}")
        print(f"平均成交价: {open_order_detail.get('price_avg')}")
    
    # 5. 市价平空订单
    print(f"\n【步骤5】提交市价平空订单（数量: {size}）")
    client_oid_close = f"{int(time.time() * 1000)}_close_short"
    
    close_order_result = place_order(
        symbol=symbol,
        client_oid=client_oid_close,
        size=str(size),
        order_type="0",  # 0: 普通订单
        match_price="1",  # 1: 市价
        price="0",  # 市价单时价格可以为0
        type_order="4"  # 4: 平空
    )
    
    if not close_order_result or not close_order_result.get('order_id'):
        print("平空订单提交失败")
        return open_order_result, None
    
    close_order_id = close_order_result.get('order_id')
    print(f"✓ 平空订单提交成功!")
    print(f"  订单ID: {close_order_id}")
    print(f"  客户端订单ID: {close_order_result.get('client_oid')}")
    
    # 6. 等待订单处理
    print(f"\n【步骤6】等待订单处理...")
    time.sleep(2)
    
    # 7. 检查确认两个订单状态
    print(f"\n【步骤7】检查确认订单状态")
    
    # 检查开仓订单
    print(f"\n开仓订单（ID: {open_order_id}）状态:")
    open_order_detail_final = get_order_detail(open_order_id)
    if open_order_detail_final:
        print(f"  状态: {open_order_detail_final.get('status')}")
        print(f"  订单类型: {open_order_detail_final.get('type')}")
        print(f"  订单数量: {open_order_detail_final.get('size')}")
        print(f"  已成交数量: {open_order_detail_final.get('filled_qty')}")
        print(f"  平均成交价: {open_order_detail_final.get('price_avg')}")
        print(f"  手续费: {open_order_detail_final.get('fee')}")
        print(f"  总盈亏: {open_order_detail_final.get('totalProfits')}")
    
    # 检查平仓订单
    print(f"\n平仓订单（ID: {close_order_id}）状态:")
    close_order_detail_final = get_order_detail(close_order_id)
    if close_order_detail_final:
        print(f"  状态: {close_order_detail_final.get('status')}")
        print(f"  订单类型: {close_order_detail_final.get('type')}")
        print(f"  订单数量: {close_order_detail_final.get('size')}")
        print(f"  已成交数量: {close_order_detail_final.get('filled_qty')}")
        print(f"  平均成交价: {close_order_detail_final.get('price_avg')}")
        print(f"  手续费: {close_order_detail_final.get('fee')}")
        print(f"  总盈亏: {close_order_detail_final.get('totalProfits')}")
    
    # 8. 获取成交明细
    print(f"\n【步骤8】获取成交明细")
    fills_open = get_order_fills(symbol=symbol, order_id=open_order_id, limit=10)
    fills_close = get_order_fills(symbol=symbol, order_id=close_order_id, limit=10)
    
    print("\n" + "="*60)
    print("市价开空并平仓流程 - 完成")
    print("="*60)
    
    return open_order_result, close_order_result


def complete_api_test(symbol="cmt_btcusdt"):
    """
    完成所有 API 测试任务（按照 WEEX Hackathon 指南）
    :param symbol: 交易对，默认 'cmt_btcusdt'
    """
    print("\n" + "="*60)
    print("WEEX API 测试流程 - 开始")
    print("="*60)
    
    # 步骤3: 检查账户余额
    print("\n【步骤3】检查账户余额")
    check_balance()
    
    # 步骤4: 设置杠杆
    print("\n【步骤4】设置杠杆（全仓模式，2倍杠杆）")
    change_leverage(symbol, 1, "2")
    
    # 步骤5: 获取资产价格
    print("\n【步骤5】获取资产价格")
    price_info = get_price(symbol)
    if price_info:
        print(f"当前价格: {price_info.get('last')}")
        print(f"24小时涨跌幅: {price_info.get('priceChangePercent')}%")
    
    # 步骤6-8: 获取价格并挂限价单（不会立即成交）
    print("\n【步骤6-8】获取当前价格并挂限价单")
    order_result = get_current_price_and_place_limit_order(
        symbol=symbol,
        size="0.01",
        order_type_direction=1,  # 开多
        price_offset_percent=20  # 价格低于市价20%，确保不会立即成交
    )
    
    if order_result and order_result.get('order_id'):
        order_id = order_result.get('order_id')
        
        # 步骤9: 获取当前挂单信息
        print("\n【步骤9】获取当前挂单信息")
        current_orders = get_current_orders(symbol=symbol)
        
        # 步骤10: 获取历史订单记录
        print("\n【步骤10】获取历史订单记录")
        create_date = int(time.time() * 1000)
        history_orders = get_order_history(symbol=symbol, page_size=10, create_date=create_date)
        
        # 步骤11: 获取成交明细
        print("\n【步骤11】获取订单成交明细")
        fills = get_order_fills(symbol=symbol, order_id=order_id, limit=10)
        
        # 取消所有挂单并验证
        print("\n" + "="*60)
        print("【清理步骤】取消所有挂单并验证")
        print("="*60)
        
        # 取消所有普通订单
        print("\n取消所有普通订单...")
        cancel_result = cancel_all_orders(cancel_order_type="normal", symbol=symbol)
        if cancel_result:
            print(f"取消结果: {cancel_result}")
        
        # 等待一下确保订单状态更新
        time.sleep(1)
        
        # 验证是否还有未撤销的订单
        print("\n验证所有订单是否已撤销...")
        remaining_orders = get_current_orders(symbol=symbol)
        
        if remaining_orders and isinstance(remaining_orders, list) and len(remaining_orders) > 0:
            print(f"警告: 仍有 {len(remaining_orders)} 个未撤销的订单")
            for order in remaining_orders:
                print(f"  - 订单ID: {order.get('order_id')}, 状态: {order.get('status')}")
            
            # 尝试再次取消
            print("\n尝试再次取消剩余订单...")
            cancel_result2 = cancel_all_orders(cancel_order_type="normal", symbol=symbol)
            time.sleep(1)
            
            # 再次验证
            remaining_orders2 = get_current_orders(symbol=symbol)
            if remaining_orders2 and isinstance(remaining_orders2, list) and len(remaining_orders2) > 0:
                print(f"仍有 {len(remaining_orders2)} 个订单未能撤销")
            else:
                print("✓ 所有订单已成功撤销")
        else:
            print("✓ 所有订单已成功撤销")
        
        print("\n" + "="*60)
        print("WEEX API 测试流程 - 完成")
        print("="*60)
    else:
        print("\n订单提交失败，无法继续后续步骤")
        
        # 即使订单提交失败，也尝试清理可能存在的挂单
        print("\n清理可能存在的挂单...")
        cancel_result = cancel_all_orders(cancel_order_type="normal", symbol=symbol)
        if cancel_result:
            print(f"取消结果: {cancel_result}")


if __name__ == '__main__':
    # 市价开空并平仓流程（0.0002，1秒后平仓）
    place_market_order_open_short_and_close("cmt_btcusdt", "0.0002", 1)
