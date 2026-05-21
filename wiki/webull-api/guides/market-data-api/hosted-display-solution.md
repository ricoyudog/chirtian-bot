---
title: Hosted Display Solution
source: https://developer.webull.hk/apis/docs/market-data-api/Hosted-Display-Solution
updated: 2026-05-17
tags: [webull, guide, market-data, hosted-display]
---

# Hosted Display Solution Documentation

## 1. Overview

A Hosted Display Solution is a professional framework that allows a Distributor to make Exchange Information or Derived Data available to an application branded or co-branded with a third-party entity for use by external subscribers.

In this model, the Distributor maintains strict control over the data, entitlements, and display of the product. The Distributor acts as the Vendor of Record (VoR), fulfilling all reporting obligations to various entities and exchanges (e.g., Nasdaq, HKEX).

## Deployment Forms

| Form | Description |
| --- | --- |
| **Widget / Iframe** | A subset of a website or platform (e.g., a stock ticker applet) |
| **White Label** | A full platform hosted or maintained by the Distributor on behalf of the third party |

## 2. 4-Step Validation Process

To ensure full compliance with exchange regulations, all implementations must undergo a mandatory validation process before production access is granted:

1. **Architecture Deliberation**
   Present a comprehensive flow diagram delineating the proposed setup and integration architecture.
2. **QA / POC Verification**
   Provide access to the relevant application or submit high-quality screenshots/video recordings for reference.
3. **Production Audit**
   Submit verification accounts and all associated URLs (Web/Mobile) for a thorough examination in alignment with regulatory requirements.
4. **Post-Launch Audit**
   The Distributor reserves the right to audit the applications post-launch to ensure continued adherence to standards.

## 3. Technical Integration: Client-to-Server (C2S)

The solution utilizes a mandatory Client-to-Server (C2S) Token Authentication model to ensure data security and entitlement integrity.

## Authentication Flow

| Step | Description |
| --- | --- |
| **Server Access Token** | The partner's backend server requests a token from the Distributor's backend using secure API credentials |
| **User Authentication** | The end-user authenticates with the partner's application |
| **Client Access Token** | The partner's backend requests a specific token for that user |
| **Data Streaming** | The client application (Frontend/App) uses the Client Access Token to establish a direct connection to the Distributor's Market Data backend via WebSocket or REST |

![Authentication Flow](https://uat-static.webullbroker.com/inst-bo/GPGIPOU7G6JK3QTPLSPCT4OP19.png)

## 4. Branding & Co-Branding Guidelines

Attribution is a mandatory requirement to ensure transparency for the end-user.

## Attribution Requirements

- **Mandatory Text**
  All pages displaying market data must feature the statement:

  > Market Data Provided by [Distributor Name]

## 5. Entitlements & Reporting

Access to real-time data is strictly regulated based on user classification and legal agreements.

- **Subscriber Agreements**
  The most updated exchange end-user agreements must be implemented within the application. Users must sign these electronically before accessing data.
- **User Bifurcation**
  Application logic must distinguish between Professional and Non-Professional users to ensure correct fee application.
- **Reporting Obligations**
  All Hosted Solution recipients must be reported in the Distributor's Detailed Report. Failure to report recipients may result in liability for providing an "Unauthorized Data Feed."
