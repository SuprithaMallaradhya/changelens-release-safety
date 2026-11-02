package com.changelens.orderapi.order;

import javax.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    private UUID id;
    @Column(nullable = false)
    private String customerId;
    @Column(nullable = false)
    private String sku;
    @Column(nullable = false)
    private int quantity;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OrderStatus status;
    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    protected Order() { }

    public Order(String customerId, String sku, int quantity) {
        this.id = UUID.randomUUID();
        this.customerId = customerId;
        this.sku = sku;
        this.quantity = quantity;
        this.status = OrderStatus.CREATED;
        this.createdAt = Instant.now();
    }

    public UUID getId() { return id; }
    public String getCustomerId() { return customerId; }
    public String getSku() { return sku; }
    public int getQuantity() { return quantity; }
    public OrderStatus getStatus() { return status; }
    public Instant getCreatedAt() { return createdAt; }
    public void reserve() { this.status = OrderStatus.RESERVED; }
    public void rejectReservation() { this.status = OrderStatus.RESERVATION_FAILED; }
}
