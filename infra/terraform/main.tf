terraform {
  required_version = ">= 1.8.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.0"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

# Generate secure database credentials
resource "random_password" "db_password" {
  length  = 32
  special = false
}

# Kubernetes Secret storing database credentials and API keys
resource "kubernetes_secret" "aegis_secrets" {
  metadata {
    name      = "aegis-secrets"
    namespace = "meridian-core"
  }

  data = {
    database-password = random_password.db_password.result
    jwt-secret-key    = "production-aegis-jwt-hmac-sha256-key-32b"
  }
}

# Helm Release deploying the Aegis Platform chart
resource "helm_release" "aegis_platform" {
  name       = "aegis-platform"
  chart      = "${path.module}/../helm/aegis-platform"
  namespace  = "meridian-core"
  create_namespace = true

  set {
    name  = "global.environment"
    value = var.environment
  }

  set {
    name  = "global.domain"
    value = var.domain_name
  }

  depends_on = [
    kubernetes_secret.aegis_secrets
  ]
}
