package com.changelens.orderapi.order;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.util.UUID;

@RestController
@RequestMapping("/orders")
@Tag(name = "Orders")
public class OrderController {
    private final OrderService service;
    public OrderController(OrderService service) { this.service = service; }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create an order")
    public OrderDtos.Response create(@Valid @RequestBody OrderDtos.CreateRequest request) {
        return new OrderDtos.Response(service.create(request.customerId, request.sku, request.quantity));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get an order")
    public OrderDtos.Response get(@PathVariable UUID id) { return new OrderDtos.Response(service.get(id)); }

    @PostMapping("/{id}/reserve")
    @Operation(summary = "Reserve inventory for an order")
    public OrderDtos.Response reserve(@PathVariable UUID id) { return new OrderDtos.Response(service.reserve(id)); }
}
