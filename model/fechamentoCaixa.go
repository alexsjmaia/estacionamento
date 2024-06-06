package model

import "time"

type FechamentoCaixa struct {
	Operador      *Operador
	NumeroDoCaixa uint8     `json:"numero_caixa"`
	Data          time.Time `json:"data"`
	TrocoInicial  float64   `json:"troco_inicial"`
	Faturamento   float64   `json:"faturamento"`
	Retirada      float64   `json:"retirada"`
	Credicard     float64   `json:"credicard"`
	Visa          float64   `json:"visa"`
	RedShop       float64   `json:"redshop"`
	VisaElectron  float64   `json:"visa_electron"`
	Outroscartoes float64   `json:"outros_cartoes"`
	Pix           float64   `json:"pix"`
	Dinheiro      float64   `json:"dinheiro"`
	TrocoFinal    float64   `json:"troco_final"`
}
