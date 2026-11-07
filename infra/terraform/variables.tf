variable "environment" {
  description = "Target deployment environment (development, staging, production)"
  type        = string
  default     = "production"
}

variable "region" {
  description = "Cloud provider target region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
  default     = "aegis-meridian-k8s"
}

variable "domain_name" {
  description = "Base domain name for Meridian banking portals and API"
  type        = string
  default     = "meridian.bank"
}

variable "postgres_version" {
  description = "PostgreSQL engine version with pgvector support"
  type        = string
  default     = "16"
}

variable "postgres_instance_class" {
  description = "Database instance compute class"
  type        = string
  default     = "db.r6g.large"
}
