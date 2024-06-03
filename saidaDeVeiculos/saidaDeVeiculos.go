// ELISA
package saidadeveiculos

import (
	"estacionamento/cobranca"
	"estacionamento/dataBase"
	impressao "estacionamento/imprimirComprovante"
	"fmt"
	"log"
	"time"
)

func SaidaDeveiculos() {

	var idProcurado int
	fmt.Printf("Digite o número da entrada:")
	fmt.Scanln(&idProcurado)

	db, err := dataBase.ConexaoBanco()
	if err != nil {
		log.Fatal("Erro ao fazer a primeira tentativa de conectar ao banco de dados para buscar veiculo cadastrado")
	}
	defer db.Close()

	var (
		id                                                  int
		placa, modelo, cor, veiculoNoPatio, dataHoraEntrada string
	)

	linha, err := db.Query("SELECT id, placa, modelo, cor, dataHoraEntrada, veiculoNoPatio FROM estacionamento.entradaDeVeiculos where id = ?", idProcurado)
	if err != nil {
		log.Fatal("Erro ao criar o statement", err)
	}
	defer linha.Close()

	if linha.Next() {
		if err := linha.Scan(&id, &placa, &modelo, &cor, &dataHoraEntrada, &veiculoNoPatio); err != nil {
			log.Fatal("Erro ao buscar a entrada do veiculo no banco", err)
		}

		if idProcurado == id {
			if veiculoNoPatio == "N" {
				fmt.Println("O Veiculo Já Saiu do Pátio")
			} else {

				linhas()

				fmt.Println("\n", placa, modelo, cor, dataHoraEntrada, veiculoNoPatio)

				dataHoraDeSaida := time.Now().Format("2006-01-02T15:04:05-07:00")

				dataHoraDeSaidaTime, err := time.Parse("2006-01-02T15:04:05-07:00", dataHoraDeSaida)
				if err != nil {
					panic(err.Error())
				}

				dataHoraEntradaTime, err := time.Parse("2006-01-02T15:04:05-07:00", dataHoraEntrada)
				if err != nil {
					panic(err.Error())
				}

				tempoDePermanencia := dataHoraDeSaidaTime.Sub(dataHoraEntradaTime)

				linhas()

				fmt.Println("\nData e hora de Entrada:\t", dataHoraEntrada)
				fmt.Println("Data e hora de saida:\t", dataHoraDeSaida)
				fmt.Println("Tempo de permanencia:\t", tempoDePermanencia)

				linhas()

				fmt.Println("")

				pagamento, valorCobrado := cobranca.Cobranca(tempoDePermanencia)

				if pagamento {
					impressao.ImprimirSaida(placa, modelo, cor, valorCobrado, int64(id))
				}
			}
		}
	}
}

func linhas() {
	for i := 0; i < 60; i++ {
		fmt.Printf("=")
	}
}
