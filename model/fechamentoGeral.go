package model

import "time"

type FechamentoGeral struct {
	Data               time.Time `json:"data"`
	TrocoInicial       FechamentoCaixa
	Faturamento        float64 `json:"faturamento"`
	DinheiroDisponivel float64 `json:"dinheiro_disponivel"`
	Retirada           float64 `json:"retirada"`
	Despesas           float64 `json:"despesas"`
	Cartoes            *FechamentoCaixa
	TrocoFinal         *FechamentoCaixa
}
