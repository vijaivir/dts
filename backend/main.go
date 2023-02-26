package main

import (
	"net/http"
	"github.com/gin-gonic/gin"
	"fmt"
//	"errors"
)


type book struct {
	ID		string `json: "id"`
	Title	string `json: "title"`
}

var books = []book{
	{ID: "1", Title:"Hunger Games"},
	{ID: "2", Title:"To kill a mocking bird"},
}

type user struct {
	username	string
}

var users = []user{
	{username: "test"},
}


func CORSMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {

        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Credentials", "true")
        c.Header("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
        c.Header("Access-Control-Allow-Methods", "POST,HEAD,PATCH, OPTIONS, GET, PUT")

        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(204)
            return
        }

        c.Next()
    }
}

func createUser(context *gin.Context) {
	//var user string
	var newuser user
	if err := context.BindJSON(&newuser); err != nil {
		fmt.Println("ERROR")
		return
	}
	users = append(users, newuser)
	fmt.Println(users)
	context.IndentedJSON(http.StatusCreated, newuser)
}


func getBooks(context *gin.Context) { 
	context.IndentedJSON(http.StatusOK, books)
}

func main() {
	router := gin.Default()
	router.Use(CORSMiddleware())
	router.GET("/books", getBooks)
	router.POST("/books", createUser)
	router.Run("localhost:8080")
}