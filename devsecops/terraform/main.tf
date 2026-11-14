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
variable "storage_account_name" {
  type        = string
  description = "Globally unique storage account for the persistent SQLite share (3-24 lowercase letters/digits)"
  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "Use 3-24 lowercase letters or digits."
  }
}
resource "azurerm_resource_group" "app" {
  name     = "rg-${var.name}"
  location = var.location
}
# Private network so the storage firewall can deny everything except the app subnet.
resource "azurerm_virtual_network" "app" {
  name                = "vnet-${var.name}"
  location            = azurerm_resource_group.app.location
  resource_group_name = azurerm_resource_group.app.name
  address_space       = ["10.20.0.0/16"]
}
resource "azurerm_subnet" "aca" {
  name                 = "snet-aca"
  resource_group_name  = azurerm_resource_group.app.name
  virtual_network_name = azurerm_virtual_network.app.name
  address_prefixes     = ["10.20.0.0/23"]
  service_endpoints    = ["Microsoft.Storage"]
  # Azure now requires the environment subnet to be delegated (workload profiles environment).
  delegation {
    name = "aca"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}
resource "azurerm_container_app_environment" "app" {
  name                     = "cae-${var.name}"
  location                 = azurerm_resource_group.app.location
  resource_group_name      = azurerm_resource_group.app.name
  infrastructure_subnet_id = azurerm_subnet.aca.id
  workload_profile {
    name                  = "Consumption" # serverless, billed per use, scales to zero
    workload_profile_type = "Consumption"
  }
}
# Persistent storage for SQLite: Azure Files share mounted at /data.
# Safe only because max_replicas = 1 (single writer); nobrl makes SQLite locking work over SMB.
resource "azurerm_storage_account" "data" {
  name                              = var.storage_account_name
  resource_group_name               = azurerm_resource_group.app.name
  location                          = azurerm_resource_group.app.location
  account_tier                      = "Standard"
  account_replication_type          = "LRS" # accepted: demo data, 7-day retention; GRS costs ~2x
  min_tls_version                   = "TLS1_2"
  https_traffic_only_enabled        = true
  allow_nested_items_to_be_public   = false
  infrastructure_encryption_enabled = true
  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    virtual_network_subnet_ids = [azurerm_subnet.aca.id]
  }
}
resource "azurerm_storage_share" "data" {
  name               = "acolhe-data"
  storage_account_id = azurerm_storage_account.data.id
  quota              = 1
}
resource "azurerm_container_app_environment_storage" "data" {
  name                         = "acolhe-data"
  container_app_environment_id = azurerm_container_app_environment.app.id
  account_name                 = azurerm_storage_account.data.name
  share_name                   = azurerm_storage_share.data.name
  access_key                   = azurerm_storage_account.data.primary_access_key
  access_mode                  = "ReadWrite"
}
resource "azurerm_container_app" "app" {
  name                         = var.name
  container_app_environment_id = azurerm_container_app_environment.app.id
  resource_group_name          = azurerm_resource_group.app.name
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"
  template {
    min_replicas = 0
    max_replicas = 1 # SQLite: never scale above one writer
    volume {
      name          = "data"
      storage_name  = azurerm_container_app_environment_storage.data.name
      storage_type  = "AzureFile"
      mount_options = "uid=10001,gid=10001,dir_mode=0700,file_mode=0600,nobrl"
    }
    container {
      name   = "acolhe"
      image  = var.image
      cpu    = 0.25
      memory = "0.5Gi"
      volume_mounts {
        name = "data"
        path = "/data"
      }
      env {
        name  = "ACOLHE_DB"
        value = "/data/acolhe.db"
      }
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
