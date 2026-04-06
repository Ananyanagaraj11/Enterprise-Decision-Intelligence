from pathlib import Path

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from core.services import PROJECT_ROOT, build_context


def dashboard(request: HttpRequest) -> HttpResponse:
    csv_rel = request.GET.get("csv", "data/ga4_public_daily.csv")
    metric = request.GET.get("metric", "revenue")
    window = int(request.GET.get("window", "14"))
    run_eval = request.GET.get("eval", "1") not in ("0", "false", "False")
    inject_n = int(request.GET.get("inject", "8"))
    seed = int(request.GET.get("seed", "42"))
    day_raw = request.GET.get("day")
    day_index = int(day_raw) if day_raw is not None and str(day_raw).isdigit() else None

    csv_path = (PROJECT_ROOT / csv_rel).resolve()
    if not csv_path.is_file():
        return render(
            request,
            "core/error.html",
            {
                "message": f"CSV not found: {csv_path}",
                "hint": "GA4 sample: python scripts/fetch_ga4_bigquery.py --out data/ga4_public_daily.csv  |  "
                "Richer e-commerce: python scripts/fetch_thelook_bigquery.py --out data/thelook_ecommerce_daily.csv",
            },
            status=404,
        )

    try:
        ctx = build_context(
            csv_path,
            metric=metric,
            window=window,
            run_eval=run_eval,
            inject_events=inject_n,
            seed=seed,
            day_index=day_index,
        )
    except Exception as e:
        return HttpResponseBadRequest(str(e))

    ctx["query"] = {
        "csv": csv_rel,
        "metric": metric,
        "window": window,
        "eval": "1" if run_eval else "0",
        "inject": inject_n,
        "seed": seed,
    }
    return render(request, "core/dashboard.html", ctx)
