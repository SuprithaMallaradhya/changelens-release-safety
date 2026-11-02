package com.changelens.orderapi.order;

import com.changelens.orderapi.inventory.InventoryClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import java.util.Optional;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock OrderRepository orders;
    @Mock InventoryClient inventory;
    @InjectMocks OrderService service;

    @Test void reservesOrderWhenInventoryAccepts() {
        Order order = new Order("customer-1", "sku-1", 2);
        when(orders.findById(order.getId())).thenReturn(Optional.of(order));
        when(inventory.reserve(order.getId(), "sku-1", 2)).thenReturn(true);
        when(orders.save(any())).thenAnswer(invocation -> invocation.getArgument(0));
        assertThat(service.reserve(order.getId()).getStatus()).isEqualTo(OrderStatus.RESERVED);
    }

    @Test void recordsFailedReservationWhenInventoryRejects() {
        Order order = new Order("customer-1", "sku-1", 2);
        when(orders.findById(order.getId())).thenReturn(Optional.of(order));
        when(inventory.reserve(order.getId(), "sku-1", 2)).thenReturn(false);
        when(orders.save(any())).thenAnswer(invocation -> invocation.getArgument(0));
        assertThat(service.reserve(order.getId()).getStatus()).isEqualTo(OrderStatus.RESERVATION_FAILED);
    }
}
