package com.changelens.orderapi.inventory;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;

import java.util.UUID;

@Component
public class InventoryClient {
    private final RestTemplate restTemplate;
    private final String baseUrl;

    public InventoryClient(RestTemplate restTemplate, @Value("${inventory.base-url:http://localhost:8081}") String baseUrl) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
    }

    public boolean reserve(UUID orderId, String sku, int quantity) {
        try {
            ReserveRequest request = new ReserveRequest(orderId, sku, quantity);
            ReserveResponse response = restTemplate.postForObject(baseUrl + "/inventory/reservations", request, ReserveResponse.class);
            return response != null && response.reserved;
        } catch (RestClientException ex) {
            return false;
        }
    }

    public static class ReserveRequest {
        public UUID orderId; public String sku; public int quantity;
        public ReserveRequest(UUID orderId, String sku, int quantity) { this.orderId = orderId; this.sku = sku; this.quantity = quantity; }
    }
    public static class ReserveResponse { public boolean reserved; }
}
