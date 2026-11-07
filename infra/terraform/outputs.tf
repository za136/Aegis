output "kubernetes_cluster_name" {
  description = "Target deployment cluster"
  value       = var.cluster_name
}

output "api_gateway_endpoint" {
  description = "Public API Gateway & MCP endpoint"
  value       = "https://api.${var.domain_name}"
}

output "customer_portal_endpoint" {
  description = "Customer Banking Portal URL"
  value       = "https://portal.${var.domain_name}"
}

output "ops_console_endpoint" {
  description = "Operations & Risk Console URL"
  value       = "https://ops.${var.domain_name}"
}
