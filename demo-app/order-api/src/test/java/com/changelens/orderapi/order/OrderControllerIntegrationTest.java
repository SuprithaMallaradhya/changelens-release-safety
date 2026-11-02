package com.changelens.orderapi.order;

import com.changelens.orderapi.inventory.InventoryClient;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import java.util.UUID;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(OrderController.class)
class OrderControllerIntegrationTest {
    @Autowired MockMvc mvc;
    @MockBean OrderService service;
    @MockBean InventoryClient inventoryClient;

    @Test void createsOrderWithValidation() throws Exception {
        Order order = new Order("customer-1", "sku-1", 2);
        when(service.create("customer-1", "sku-1", 2)).thenReturn(order);
        mvc.perform(post("/orders").contentType(MediaType.APPLICATION_JSON)
                .content("{\"customerId\":\"customer-1\",\"sku\":\"sku-1\",\"quantity\":2}"))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.id").value(order.getId().toString()))
                .andExpect(jsonPath("$.status").value("CREATED"));
    }

    @Test void rejectsInvalidQuantity() throws Exception {
        mvc.perform(post("/orders").contentType(MediaType.APPLICATION_JSON)
                .content("{\"customerId\":\"customer-1\",\"sku\":\"sku-1\",\"quantity\":0}"))
                .andExpect(status().isBadRequest());
    }
}
