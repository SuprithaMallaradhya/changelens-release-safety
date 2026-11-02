package com.changelens.orderapi.order;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import java.time.Instant;
import java.util.UUID;

public final class OrderDtos {
    private OrderDtos() { }

    public static class CreateRequest {
        @NotBlank public String customerId;
        @NotBlank public String sku;
        @Min(1) public int quantity;
    }

    public static class Response {
        public UUID id;
        public String customerId;
        public String sku;
        public int quantity;
        public OrderStatus status;
        public Instant createdAt;

        public Response(Order order) {
            id = order.getId(); customerId = order.getCustomerId(); sku = order.getSku();
            quantity = order.getQuantity(); status = order.getStatus(); createdAt = order.getCreatedAt();
        }
    }
}
