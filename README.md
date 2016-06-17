# WooCommerce-Xero-Integration
A simple Python utility that uses the Xero API and the WC API to keep product and customer data in sync.

## Setup Instructions

### Set up Xero API

Follow these instructions to set up a private Xero application using a public / private key pair: https://developer.xero.com/documentation/getting-started/private-applications/
Copy the client key and secret from the api manager into a copy of the example xero yaml config file along with the path to the private key file you generated

### Set up WC API

Follow instructions for generating your client key / secret pair from WooCommerce
Copy the client key and secret from the WooCommerce into a copy of the example wc yaml config file along with the store url

### Set up Application dependencies

Install python 2.7, then install the following dependencies using pip2

tabulate kitchen woocommerce pyxero
