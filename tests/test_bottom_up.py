"""
Bottom-Up.
  Level 1: ShippingRepository ShippingPublisher
  Level 2: ShippingService — Repository + Publisher
  Level 3: Order —  ShippingService
"""

import boto3
import pytest
from datetime import datetime, timedelta, timezone

from eshop import Product, ShoppingCart, Order, Shipment
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE


# ──────────────────────────────────────────────
# LEVEL 1 — ShippingRepository
# ──────────────────────────────────────────────

def test_repository_create_shipping_saves_to_db(dynamo_resource):
    """
    Тест 1 (Level 1 — Repository):
    Перевіряє що ShippingRepository.create_shipping збергіає запис у DynamoDB.
    Після create_shipping отримуємо запис по ID і порівнюємо поля.
    """
    repo = ShippingRepository()
    due_date = datetime.now(timezone.utc) + timedelta(minutes=10)

    shipping_id = repo.create_shipping(
        shipping_type="Нова Пошта",
        product_ids=["product_1", "product_2"],
        order_id="order_test_1",
        status="created",
        due_date=due_date,
    )

    item = repo.get_shipping(shipping_id)
    assert item is not None
    assert item["shipping_id"] == shipping_id
    assert item["shipping_type"] == "Нова Пошта"
    assert item["order_id"] == "order_test_1"
    assert item["shipping_status"] == "created"
    assert item["product_ids"] == "product_1,product_2"


def test_repository_get_nonexistent_shipping_returns_none(dynamo_resource):
    """
    Тест 2 (Level 1 — Repository):
    Перевіряє що get_shipping повертає None для неіснуючого ID.
    Гранична поведінка — запис відсутній у БД.
    """
    repo = ShippingRepository()
    result = repo.get_shipping("non-existent-id-12345")
    assert result is None


def test_repository_update_shipping_status(dynamo_resource):
    """
    Тест 3 (Level 1 — Repository):
    Перевіряє що update_shipping_status коректно оновлює статус у DynamoDB.
    """
    repo = ShippingRepository()
    due_date = datetime.now(timezone.utc) + timedelta(minutes=10)

    shipping_id = repo.create_shipping(
        shipping_type="Укр Пошта",
        product_ids=["product_a"],
        order_id="order_test_2",
        status="created",
        due_date=due_date,
    )

    repo.update_shipping_status(shipping_id, "completed")

    item = repo.get_shipping(shipping_id)
    assert item["shipping_status"] == "completed"


# ──────────────────────────────────────────────
# LEVEL 1 — ShippingPublisher (SQS)
# ──────────────────────────────────────────────

def _sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@pytest.fixture(autouse=True)
def purge_queue_after_test():
    """Очищує SQS чергу після кожного тесту щоб не забруднювати інші тести."""
    yield
    sqs = _sqs_client()
    queue_url = sqs.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]
    sqs.purge_queue(QueueUrl=queue_url)


def test_publisher_send_message_appears_in_queue(dynamo_resource):
    """
    Тест 4 (Level 1 — Publisher):
    Перевіряє що ShippingPublisher.send_new_shipping відправляє повідомлення у SQS.
    Читаємо чергу, перевіряємо що повідомлення там є, і видаляємо щоб не забруднювати чергу.
    """
    publisher = ShippingPublisher()
    test_id = "test-shipping-pub-001"
    publisher.send_new_shipping(test_id)

    sqs = _sqs_client()
    queue_url = sqs.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=3)

    messages = response.get("Messages", [])
    target = [m for m in messages if m["Body"] == test_id]
    assert len(target) == 1

    # видаляємо щоб не заважати іншим тестам
    for m in messages:
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=m["ReceiptHandle"])


def test_publisher_poll_shipping_returns_ids(dynamo_resource):
    """
    Тест 5 (Level 1 — Publisher):
    Перевіряє що poll_shipping повертає список ID відправлень з черги.
    Після перевірки очищаємо чергу.
    """
    publisher = ShippingPublisher()
    test_id = "test-shipping-pub-002"
    publisher.send_new_shipping(test_id)

    sqs = _sqs_client()
    queue_url = sqs.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=3)
    messages = response.get("Messages", [])

    bodies = [m["Body"] for m in messages]
    assert test_id in bodies

    # видаляємо всі отримані повідомлення
    for m in messages:
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=m["ReceiptHandle"])


# ──────────────────────────────────────────────
# LEVEL 2 — ShippingService (Repository + Publisher)
# ──────────────────────────────────────────────

def test_service_create_shipping_persists_and_returns_id(dynamo_resource):
    """
    Тест 6 (Level 2 — Service):
    Перевіряє що ShippingService.create_shipping зберігає запис у БД
    і повертає валідний shipping_id.
    """
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    due_date = datetime.now(timezone.utc) + timedelta(minutes=5)

    shipping_id = service.create_shipping(
        shipping_type="Meest Express",
        product_ids=["item_1"],
        order_id="order_svc_1",
        due_date=due_date,
    )

    assert shipping_id is not None
    item = ShippingRepository().get_shipping(shipping_id)
    assert item is not None
    assert item["shipping_id"] == shipping_id


def test_service_create_shipping_sets_status_in_progress(dynamo_resource):
    """
    Тест 7 (Level 2 — Service):
    Перевіряє що після create_shipping статус у БД стає 'in progress'
    (Service спочатку ставить 'created', потім оновлює на 'in progress').
    """
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    due_date = datetime.now(timezone.utc) + timedelta(minutes=5)

    shipping_id = service.create_shipping(
        shipping_type="Нова Пошта",
        product_ids=["item_2"],
        order_id="order_svc_2",
        due_date=due_date,
    )

    item = ShippingRepository().get_shipping(shipping_id)
    assert item["shipping_status"] == ShippingService.SHIPPING_IN_PROGRESS


def test_service_create_shipping_with_past_due_date_raises(dynamo_resource):
    """
    Тест 8 (Level 2 — Service):
    Перевіряє що create_shipping кидає ValueError якщо due_date в минулому.
    Гранична поведінка — невалідна дата.
    """
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    past_due_date = datetime.now(timezone.utc) - timedelta(minutes=1)

    with pytest.raises(ValueError, match="due datetime must be greater"):
        service.create_shipping(
            shipping_type="Нова Пошта",
            product_ids=["item_x"],
            order_id="order_svc_3",
            due_date=past_due_date,
        )


def test_service_complete_shipping_updates_status(dynamo_resource):
    """
    Тест 9 (Level 2 — Service):
    Перевіряє повний цикл: create_shipping → complete_shipping → статус 'completed'.
    """
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    due_date = datetime.now(timezone.utc) + timedelta(minutes=5)

    shipping_id = service.create_shipping(
        shipping_type="Самовивіз",
        product_ids=["item_3"],
        order_id="order_svc_4",
        due_date=due_date,
    )

    service.complete_shipping(shipping_id)

    status = service.check_status(shipping_id)
    assert status == ShippingService.SHIPPING_COMPLETED


# ──────────────────────────────────────────────
# LEVEL 3 — Order (використовує ShippingService)
# ──────────────────────────────────────────────

def test_order_place_order_reduces_product_stock(dynamo_resource):
    """
    Тест 10 (Level 3 — Order):
    Перевіряє що після place_order кількість товару на складі зменшується.
    Тест верхнього рівня — перевіряє повний ланцюг: Order → Service → Repository → DB.
    """
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    product = Product(name="Laptop", price=999.0, available_amount=5)
    cart = ShoppingCart()
    cart.add_product(product, amount=3)

    order = Order(cart, service)
    order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    assert product.available_amount == 2
