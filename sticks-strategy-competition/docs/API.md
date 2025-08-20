# API Documentation for Sticks Strategy Competition

## Overview

This document provides an overview of the API used in the Sticks Strategy Competition dashboard. The API allows users to interact with the tournament data, retrieve statistics, and manage player strategies.

## Endpoints

### 1. Get Tournament Statistics

- **URL**: `/api/stats`
- **Method**: `GET`
- **Description**: Retrieves the current statistics of the tournament, including player performance and match results.
- **Response**:
  - `200 OK`: Returns a JSON object containing the statistics.
  - `404 Not Found`: If no statistics are available.

### 2. Submit Strategy

- **URL**: `/api/strategies`
- **Method**: `POST`
- **Description**: Submits a new player strategy to the competition.
- **Request Body**:
  - `strategy_file`: The Python file containing the strategy implementation.
- **Response**:
  - `201 Created`: If the strategy is successfully submitted.
  - `400 Bad Request`: If the strategy does not conform to the required format.

### 3. Get Strategy Details

- **URL**: `/api/strategies/{strategy_id}`
- **Method**: `GET`
- **Description**: Retrieves details of a specific strategy by its ID.
- **Response**:
  - `200 OK`: Returns a JSON object with strategy details.
  - `404 Not Found`: If the strategy ID does not exist.

### 4. Get Match History

- **URL**: `/api/matches`
- **Method**: `GET`
- **Description**: Retrieves the history of matches played in the tournament.
- **Response**:
  - `200 OK`: Returns a JSON array of match records.
  - `404 Not Found`: If no match history is available.

## Error Handling

All API responses include an error message in the case of failure. The structure of the error response is as follows:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message."
  }
}
```

## Conclusion

This API provides essential functionality for managing and interacting with the Sticks Strategy Competition. For further details on how to implement strategies, please refer to the `STRATEGY_SPEC.md` document.