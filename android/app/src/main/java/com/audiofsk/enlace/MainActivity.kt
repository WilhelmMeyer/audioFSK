package com.audiofsk.enlace

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.ScrollView
import android.widget.TextView
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject
import java.io.File
import kotlin.concurrent.thread

class MainActivity : Activity() {
    private lateinit var diario: TextView
    private lateinit var rolagem: ScrollView
    private lateinit var situacao: TextView
    private lateinit var recebido: TextView
    private lateinit var texto: EditText
    private lateinit var iniciar: Button
    private lateinit var parar: Button
    private lateinit var enviar: Button
    private lateinit var repetir: Button
    private lateinit var ouvinte: RadioButton
    @Volatile private var sessao: PyObject? = null

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))
        monta()
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), 1)
        linha("[app] protocolo ${BuildConfig.PROTOCOLO}; gravações em ${pasta()}")
    }

    private fun monta() {
        val raiz = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 24, 24, 24)
            fitsSystemWindows = true
        }
        ouvinte = RadioButton(this).apply { text = "ouvinte"; id = View.generateViewId() }
        val chamador = RadioButton(this).apply { text = "chamador"; id = View.generateViewId() }
        raiz.addView(RadioGroup(this).apply {
            orientation = RadioGroup.HORIZONTAL
            addView(ouvinte); addView(chamador); check(ouvinte.id)
        })
        texto = EditText(this).apply { hint = "texto a enviar"; setSingleLine() }
        raiz.addView(texto)
        val botoes = LinearLayout(this)
        iniciar = Button(this).apply { text = "Iniciar"; setOnClickListener { inicia() } }
        parar = Button(this).apply { text = "Parar"; isEnabled = false
            setOnClickListener { sessao?.put("parar", true) } }
        enviar = Button(this).apply { text = "Enviar"; isEnabled = false
            setOnClickListener { sessao?.callAttr("envia", texto.text.toString()); texto.setText("") } }
        repetir = Button(this).apply { text = "Repetir"; setOnClickListener { repete() } }
        listOf(iniciar, parar, enviar, repetir).forEach { botoes.addView(it) }
        raiz.addView(botoes)
        situacao = TextView(this)
        recebido = TextView(this)
        raiz.addView(situacao); raiz.addView(recebido)
        diario = TextView(this).apply { textSize = 11f; setTextIsSelectable(true) }
        rolagem = ScrollView(this).apply { addView(diario) }
        raiz.addView(rolagem, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f))
        setContentView(raiz)
    }

    private fun pasta(): File = File(getExternalFilesDir(null), "sessoes").apply { mkdirs() }

    private fun linha(s: String) = runOnUiThread {
        diario.append(s + "\n")
        rolagem.post { rolagem.fullScroll(View.FOCUS_DOWN) }
    }

    private fun mostra(j: String) = runOnUiThread {
        val e = JSONObject(j)
        situacao.text = "etapa ${e.optString("etapa")}  aberto ${e.optBoolean("aberto")}  " +
            "tempo ${e.optDouble("estacao_s")} s  rms ${e.optDouble("rms")}\n" +
            "fila ${e.optDouble("fila_s")} s  passo ${e.optDouble("passo_ms")} ms  " +
            "perdida ${e.optDouble("perdidas_s")} s  a enviar ${e.optInt("a_enviar")}  recebidos ${e.optInt("recebidos")}"
        recebido.text = e.optString("texto")
    }

    private fun emSessao(ligada: Boolean) = runOnUiThread {
        iniciar.isEnabled = !ligada; repetir.isEnabled = !ligada
        parar.isEnabled = ligada; enviar.isEnabled = ligada
    }

    private fun inicia() {
        val papel = if (ouvinte.isChecked) "ouvinte" else "chamador"
        val inicial = texto.text.toString()
        texto.setText("")
        emSessao(true)
        thread(name = "estacao") {
            var ponte: Ponte? = null
            try {
                ponte = Ponte(this, ::linha, ::mostra)
                linha("[app] carregando a estação...")
                val s = Python.getInstance().getModule("movel")
                    .callAttr("Sessao", papel, pasta().path, ponte, inicial)
                ponte.abre()
                sessao = s
                s.callAttr("roda")
            } catch (e: Throwable) {
                linha("[app] ERRO: $e")
            } finally {
                sessao = null
                ponte?.fecha()
                emSessao(false)
            }
        }
    }

    /** `replay.wav` posto na pasta do app: o diário sai em `replay.txt`, para comparar com o PC. */
    private fun repete() {
        val wav = File(getExternalFilesDir(null), "replay.wav")
        if (!wav.exists()) { linha("[app] falta $wav"); return }
        val papel = if (ouvinte.isChecked) "ouvinte" else "chamador"
        emSessao(true); parar.isEnabled = false; enviar.isEnabled = false
        thread(name = "repete") {
            try {
                val r = Python.getInstance().getModule("movel").callAttr("repete", wav.path, papel,
                    File(getExternalFilesDir(null), "replay.txt").path)
                linha("[app] repetição: $r")
            } catch (e: Throwable) {
                linha("[app] ERRO: $e")
            } finally {
                emSessao(false)
            }
        }
    }
}
