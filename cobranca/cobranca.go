package cobranca

import (
	"estacionamento/dataBase"
	"fmt"
	"log"
	"time"
)

var (
	valorCobrado, valorPrimeiraHora, valorHoraAdicional, valorDiaria float64
	tempoDePermanenciaMinutos, id                                    int
)

func Cobranca(tempoDePermanencia time.Duration) {
	db, erro := dataBase.ConexaoBanco()
	if erro != nil {
		log.Fatal("Erro co conectar ao banco de dados")
	}
	defer db.Close()

	linha, err := db.Query("SELECT * FROM estacionamento.valoresDeCobranca where id = 1")
	if err != nil {
		log.Fatal("Erro ao criar o statement cobrança", err)
	}
	defer linha.Close()

	if linha.Next() {
		if err := linha.Scan(&id, &valorPrimeiraHora, &valorHoraAdicional, &valorDiaria); err != nil {
			log.Fatal("Erro ao buscar os valores no banco", err)
		}
	}

	tempoDePermanenciaMinutos := int(tempoDePermanencia.Minutes())

	if tempoDePermanenciaMinutos < 60 {
		valorCobrado = valorPrimeiraHora
		mostraValorCobrado(valorCobrado)

	} else if tempoDePermanenciaMinutos < 120 {
		valorCobrado = valorPrimeiraHora + valorHoraAdicional
		mostraValorCobrado(valorCobrado)

	} else if tempoDePermanenciaMinutos < 180 {
		valorCobrado = valorPrimeiraHora + (valorHoraAdicional * 2)
		mostraValorCobrado(valorCobrado)

	} else {
		valorCobrado = valorDiaria
		mostraValorCobrado(valorCobrado)
	}

	hours := int(tempoDePermanencia.Hours())
	minutes := int(tempoDePermanencia.Minutes()) % 60
	seconds := int(tempoDePermanencia.Seconds()) % 60

	fmt.Printf("Tempo de permanência do Veiculo %02d:%02d:%02d\n", hours, minutes, seconds)
	formaDePagamento(valorCobrado)
}

func mostraValorCobrado(valorCobrado float64) {
	fmt.Printf("Valor Total R$ %.2f\n", valorCobrado)
}
