package impressao

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"time"
)

func ImprimirSaida(pla, modelo, cor string, valorCobrado float64, id int64) {

	file, erro := os.Create("plas.txt")
	if erro != nil {
		log.Fatal("Falha ao Criar Arquivo Para Impressão", erro)
	}

	defer file.Close()

	len, erro := file.WriteString("===================================\n" +
		"===================================\n" +
		"\n * * * ESTACIONAMENTO * * *\n\n" +
		"CNPJ : 00.000.000/0000-00\n" +
		"Rua Dos bobos, 0 CEP : 00000-000\n\n" +
		"COMPROVANTE DE ENTRADA DE VEICULO\n\n" +
		"SAO PAULO " + time.Now().Format("02/01/2006 15:04:05\n\n") +
		"ENTRADA : " + fmt.Sprintf("%d", id) + "\n" +
		"DATA E HORA DE ENTRADA : " + time.Now().Format("02/01/2006 15:04:05\n\n") +
		"\tPLACA : " + pla + "\n" +
		"\tMODELO : " + modelo + "\n" +
		"\tCOR : " + cor + "\n" +
		"\tVALOR COBRADO : " + fmt.Sprint(valorCobrado) + "\n" +
		"===================================\n" +
		"===================================\n\n\n\n\n\n" +
		"\n\n\n\n\n\n.")

	if erro != nil {
		log.Fatalf("Falha ao Criar Arquivo: %s", erro)
	}

	cmd = exec.Command("bash", "/usr/local/estac/main/plas.sh")
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		fmt.Println("Imprimindo...")
		return
	} else {
		fmt.Println("Execute a reimpressão")
	}

	fmt.Printf("\nTamanho do Arqivo : %d bytes", len)
}

func Sprintf(valorCobrado float64) {
	panic("unimplemented")
}
