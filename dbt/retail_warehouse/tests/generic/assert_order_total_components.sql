{% test assert_order_total_components(model, total_col, subtotal_col, discount_col, tax_col, shipping_col, tolerance=0.02) %}

select
    {{ model }}.{{ total_col }}      as total_amount,
    {{ model }}.{{ subtotal_col }}   as subtotal_amount,
    {{ model }}.{{ discount_col }}   as discount_amount,
    {{ model }}.{{ tax_col }}        as tax_amount,
    {{ model }}.{{ shipping_col }}   as shipping_amount,
    abs(
        {{ model }}.{{ total_col }}
        - (
            {{ model }}.{{ subtotal_col }}
            - {{ model }}.{{ discount_col }}
            + {{ model }}.{{ tax_col }}
            + {{ model }}.{{ shipping_col }}
          )
    )                                as deviation
from {{ model }}
where
    abs(
        {{ model }}.{{ total_col }}
        - (
            {{ model }}.{{ subtotal_col }}
            - {{ model }}.{{ discount_col }}
            + {{ model }}.{{ tax_col }}
            + {{ model }}.{{ shipping_col }}
          )
    ) > {{ tolerance }}

{% endtest %}
