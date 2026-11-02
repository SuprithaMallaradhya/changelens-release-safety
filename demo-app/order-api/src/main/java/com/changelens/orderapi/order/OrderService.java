package com.changelens.orderapi.order;

import com.changelens.orderapi.inventory.InventoryClient;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.transaction.annotation.Transactional;
import java.util.UUID;

@Service
public class OrderService {
    private final OrderRepository orders;
    private final InventoryClient inventory;

    public OrderService(OrderRepository orders, InventoryClient inventory) { this.orders = orders; this.inventory = inventory; }
    public Order create(String customerId, String sku, int quantity) { return orders.save(new Order(customerId, sku, quantity)); }
    @Transactional(readOnly = true)
    public Order get(UUID id) { return orders.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Order not found")); }
    @Transactional
    public Order reserve(UUID id) {
        Order order = get(id);
        if (order.getStatus() == OrderStatus.RESERVED) return order;
        if (inventory.reserve(id, order.getSku(), order.getQuantity())) order.reserve(); else order.rejectReservation();
        return orders.save(order);
    }
}
