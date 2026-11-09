terraform {
  required_version = ">= 1.6, < 2.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
variable "subscription_id" {
  type        = string
  description = "Azure subscription explicitly authorized for deployment"
}
variable "location" {
  type    = string
  default = "brazilsouth"
}
variable "name" {
  type    = string
  default = "acolhe-demo"
}
variable "image" {
  type        = string
  description = "Public immutable OCI image reference, preferably @sha256 digest"
}
resource "azurerm_resource_group" "app" {
  name     = "rg-${var.name}"
  location = var.location
}
resource "azurerm_container_app_environment" "app" {
  name                = "cae-${var.name}"
  location            = azurerm_resource_group.app.location
  resource_group_name = azurerm_resource_group.app.name
}
resource "azurerm_container_app" "app" {
  name                         = var.name
  container_app_environment_id = azurerm_container_app_environment.app.id
  resource_group_name          = azurerm_resource_group.app.name
  revision_mode                = "Single"
  template {
    min_replicas = 0
    max_replicas = 1
    container {
      name   = "acolhe"
      image  = var.image
      cpu    = 0.25
      memory = "0.5Gi"
      env {
        name  = "HOST"
        value = "0.0.0.0"
      }
      env {
        name  = "ROBOT_MODE"
        value = "simulate"
      }
    }
  }
  ingress {
    external_enabled           = true
    target_port                = 8080
    transport                  = "http"
    allow_insecure_connections = false
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}
output "url" {
  value = "https://${azurerm_container_app.app.ingress[0].fqdn}"
}
