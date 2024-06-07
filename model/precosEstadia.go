package model

type precosEstadia struct {
	ID            int64   `id:"id"`
	PrimeiraHora  float64 `json:"primeira_hora"`
	HoraAdicional float64 `json:"hora_adicional"`
	Diaria        float64 `json:"diaria"`
	Mensalidade   float64 `json:"mensalidade"`
}
