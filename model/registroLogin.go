package model

import "time"

type RegistroLogin struct {
	ID      uint64    `json:"id"`
	Cod     uint64    `json:"cod"`
	Usuario string    `json:"usuario"`
	Data    time.Time `json:"data_hora"`
}
