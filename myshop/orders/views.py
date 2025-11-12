from django.shortcuts import render, redirect
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import OrderItem, Order
from django.contrib.auth.decorators import login_required
from .tasks import order_created

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
            # clear the cart
            cart.clear()
            # Launch asynchronous task
            order_created.delay(order.id)
            # set the order in the session
            request.session['order_id'] = order.id
            # redirect to the payment
            return redirect('payment:process')
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order/list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'orders/order/detail.html', {'order': order})

@login_required
def order_confirm(request, order_id):
    order = Order.objects.get(id=order_id)
    order.status = 'confirmed'
    order.save()
    return redirect('order_detail', order_id=order_id)
