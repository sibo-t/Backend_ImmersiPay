package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
)

// Define the context for Redis operations.
var ctx = context.Background()

// Session represents a user's session data.
type Session struct {
	ID        string `json:"id"`
	CreatedAt time.Time `json:"created_at"`
	CartData  map[string]interface{} `json:"cart_data"`
}

// PaymentRequest is a simplified structure for an incoming payment request.
type PaymentRequest struct {
	SessionID     string  `json:"session_id"`
	MerchantID    string  `json:"merchant_id"`
	TransactionID string  `json:"transaction_id"`
	Amount        float64 `json:"amount"`
	Currency      string  `json:"currency"`
	CardToken     string `json:"card_token"`
}

// PaymentResponse is the structure for the response sent back to the merchant.
type PaymentResponse struct {
	TransactionID string `json:"transaction_id"`
	Status        string `json:"status"`
	Message       string `json:"message"`
}

// redisClient is the Redis client instance.
var redisClient *redis.Client

// init function to connect to Redis when the application starts.
func init() {
	redisClient = redis.NewClient(&redis.Options{
		Addr:     "localhost:6379", // Use your Redis server address
		Password: "",               // No password set
		DB:       0,                // Use default DB
	})

	// Ping Redis to ensure the connection is working.
	pong, err := redisClient.Ping(ctx).Result()
	if err != nil {
		log.Fatalf("Could not connect to Redis: %v", err)
	}
	fmt.Println("Successfully connected to Redis:", pong)
}

// processPayment handles the payment processing logic with Redis session validation.
func processPayment(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var req PaymentRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Check if the session ID exists in Redis.
	sessionJSON, err := redisClient.Get(ctx, req.SessionID).Result()
	if err == redis.Nil {
		// Redis returns redis.Nil if the key does not exist.
		http.Error(w, "Invalid or expired session ID", http.StatusUnauthorized)
		return
	} else if err != nil {
		http.Error(w, "Error retrieving session from Redis", http.StatusInternalServerError)
		return
	}

	// Unmarshal the session data from JSON.
	var session Session
	if err := json.Unmarshal([]byte(sessionJSON), &session); err != nil {
		http.Error(w, "Failed to unmarshal session data", http.StatusInternalServerError)
		return
	}

	fmt.Printf("Processing payment for session %s and Merchant %s\n", session.ID, req.MerchantID)

	// Simulate a successful transaction.
	status := "success"
	message := "Transaction approved"

	response := PaymentResponse{
		TransactionID: req.TransactionID,
		Status:        status,
		Message:       message,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
}

func main() {
	http.HandleFunc("/process-payment", processPayment)

	fmt.Println("Payment Gateway server listening on :8080...")
	log.Fatal(http.ListenAndServe(":8080", nil))
}