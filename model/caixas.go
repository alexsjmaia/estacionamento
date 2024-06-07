package model

import "time"

type caixas struct {
	NumeroDoCaixa uint8     `json:"numero_caixa"`
	Data          time.Time `json:"data"`
	Troco         float64   `json:"troco"`
}
