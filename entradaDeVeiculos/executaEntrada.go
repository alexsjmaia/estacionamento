package entradaDeVeiculos

import (
	"estacionamento/dataBase"
	"fmt"
	"log"
	"time"
)

// VeiculoNoPatio Verificar se o Veiculo já está no patio e etorna True para não repetir a entrada
func VeiculoNoPatio(placa string) bool {

	// Capturando a data atual do sistema e guardando na variavel dataDeEntrada
	ano, mes, dia := time.Now().Date()
	hoje := fmt.Sprintf("%d-%02d-%02d", ano, mes, dia)

	db, err := dataBase.ConexaoBanco()
	if err != nil {
		log.Fatal("Erro ao fazer a primeira tentativa de conectar ao banco de dados para buscar veiculo cadastrado")
	}
	defer db.Close()

	linha, err := db.Query("SELECT * FROM estacionamento.entradaDeVeiculos where placa = ?", placa)
	if err != nil {
		log.Fatal("Erro ao criar o statement")
	}
	defer linha.Close()

	id := ""
	modelo := ""
	cor := ""
	dataHoraEntrada := ""
	veiculoNoPatio := ""

	if linha.Next() {
		if err := linha.Scan(&id, &placa, &modelo, &cor, &dataHoraEntrada, &veiculoNoPatio); err != nil {
			log.Fatal("Erro ao buscar a entrada do veiculo no banco", err)
		}
		dataDeEntrada := fmt.Sprintf("%d-%02d-%02d", ano, mes, dia)

		if veiculoNoPatio == "S" {
			if hoje == dataDeEntrada {
				return true
			}
		}
	}
	return false
}

// ExecutaEntrada grava os dados de entrada no banco
func ExecutaEntrada(placa, modelo, cor string) int {
	verifica := VeiculoNoPatio(placa)

	if verifica {
		fmt.Println("O Veiculo ainda está no pátio")
		return 0
	}

	fmt.Println("Executando a Entrada do Veiculo!", placa, modelo, cor)

	db, erro := dataBase.ConexaoBanco()
	if erro != nil {
		log.Fatal("Erro co conectar ao banco de dados")
	}
	defer db.Close()

	statement, err := db.Prepare("insert into entradaDeVeiculos (placa, modelo, cor, dataHoraEntrada, veiculoNoPatio) values (?, ?, ?, ?, ?)")

	if err != nil {
		fmt.Println("Erro ao Criar o statement", erro)
		return 0
	}
	defer statement.Close()

	// Capturando a data atual do sistema e guardando na variavel dataDeEntrada
	//ano, mes, dia := time.Now().Date()
	//dataDeEntrada := fmt.Sprintf("%d-%02d-%02d", ano, mes, dia)

	// Capturando a hora atual do sistema e guardando na variavel horaDeEntrada
	dataHoraEntrada := time.Now()

	veiculoNoPatio := "S"

	insercao, erro := statement.Exec(placa, modelo, cor, dataHoraEntrada, veiculoNoPatio)

	if erro != nil {
		fmt.Println("Erro ao Montar a Inserção", insercao)
		fmt.Println(erro.Error())
		return 0
	}

	idInserido, erro := insercao.LastInsertId()
	if erro != nil {
		fmt.Println("Erro ao Obter o Numero da Entrada")
	}

	fmt.Println("Carro inserido com sucesso", idInserido)
	return int(idInserido)

}
